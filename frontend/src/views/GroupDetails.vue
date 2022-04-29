<template>
  <div class="group-details">
    <top-bar title="Group Details"></top-bar>
    <error-message v-if="localState.error" :error="localState.error"></error-message>
    <v-container v-if="localState.group">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-row>
            <v-col>
              <h1 class="justify-center d-flex">
                {{localState.group.name}}
              </h1>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input 
                label="Email" 
                field="email"
                :obj="localState.group"
                action="groups/update"
                :readonly="!canEdit"
                @updated="localState.group=$event"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input 
                label="Description" 
                field="description"
                :obj="localState.group"
                action="groups/update"
                :readonly="!canEdit"
                @updated="localState.group=$event"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col>
              <hsk-text-input label="Collections" :static-value="localState.group.collections"></hsk-text-input>
            </v-col>
            <v-col>
              <hsk-text-input v-if="localState.entity" label="Used Quota" :static-value="localState.entity.usedQuota | prettyBytes"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col>
              <hsk-text-input label="Created" :static-value="localState.group.createdAt | prettyDateTime"></hsk-text-input>
            </v-col>
            <v-col>
              <hsk-text-input label="Created By" :static-value="localState.group.createdBy"></hsk-text-input>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <h3>Members</h3>
          <v-data-table
            id="members"
            :headers="headers"
            :items="localState.group.users"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading"
            >
            <template v-slot:top>
              <v-toolbar flat>
                <v-text-field 
                  v-model="localState.search" 
                  prepend-inner-icon="mdi-magnify" 
                  label="Search..." 
                  single-line outlined dense hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog max-width="700px" v-model="localState.showAdd" v-if="canEdit">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn
                      dense depressed
                      v-bind="attrs" v-on="on">Add Member</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">Add Member</v-card-title>
                    <v-card-text>
                      <v-form v-model="localState.editValid">
                        <hsk-user-input
                          required
                          label="Username"
                          v-model="localState.editItem.user.username"></hsk-user-input>
                        <hsk-text-input
                          id="role"
                          label="Role"
                          type="select"
                          field="role"
                          :obj="localState.editItem"
                          required
                          :options="availableRoles"
                          @updated="localState.editItem=$event"
                        ></hsk-text-input>
                      </v-form>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeAdd">Mabye not today.</v-btn>
                      <v-btn color="primary darken-1" :disabled="!localState.editValid" text @click="addUser">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </v-toolbar>
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot --> 
            <template v-slot:item.user.username="{ item }">
              {{item.user.username}}
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot --> 
            <template v-slot:item.user.lastname="{ item }">
              {{item.user.firstname}} {{item.user.lastname}}
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot --> 
            <template v-slot:item.role="{ item }">
              <hsk-text-input
                id="role"
                label=""
                type="select"
                field="role"
                :obj="item"
                required
                inline
                :readonly="!canEdit"
                :options="availableRoles"
                @updated="updateRole($event)"
              ></hsk-text-input>
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot --> 
            <template v-slot:item.actions="{ item }">
              <v-icon v-if="canEdit" small @click="deleteUser(item)">mdi-delete</v-icon>
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { DataTableHeader } from 'vuetify';
import { Entity, Group, GroupMember, GroupRoles, User } from '../store/models';
import UserInput from '@/components/UserInput.vue';
import { concat as _concat, filter as _filter } from 'lodash';

interface State {
  group: Group | null;
  entity: Entity | null;
  error: string | null;
  search: string;
  sortBy: string;
  sortDesc: boolean;
  editValid: boolean;
  showAdd: boolean;
  editItem: GroupMember;
}

function defaultItem(): GroupMember {
  const item = new GroupMember();
  item.role = GroupRoles.contributor;
  item.user = new User();
  item.user.username = '';
  return item;
}

export default Vue.extend({
  name: 'GroupDetails',
  components: { 'hsk-user-input': UserInput },
  mounted() {
    this.loadGroup();
  },
  data: (): { headers: DataTableHeader[]; localState: State } => ({
    headers: [
      { text: 'Username', value: 'user.username', sortable: true },
      { text: 'Name', value: 'user.lastname', sortable: true },
      { text: 'Role', value: 'role', sortable: true },
      { text: 'Actions', value: 'actions', sortable: false, filterable: false, width: '10%' },
    ],
    localState: {
      group: null,
      entity: null,
      error: null,
      search: '',
      sortBy: 'user.username',
      sortDesc: false,
      showAdd: false,
      editValid: true,
      editItem: defaultItem(),
    }
  }),
  watch: {
    $route() {
      this.loadGroup();
    }
  },
  computed: {
    loading(): boolean {
      return this.$store.getters['groups/status']==='loading';
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return this.localState.group !== null && this.localState.group.canEdit(this.currentUser)
    },
    availableRoles(): Record<string, unknown>[] {
      return Object.keys(GroupRoles).map(r => {
        return { value: r, text: r };
      });
    }
  },
  methods: {
    loadGroup() {
      this.localState.error = null;
      this.$store.dispatch('groups/get', this.$route.params.group)
        .then((group: Group) => {
          this.localState.group = group;
          return this.$store.dispatch('entities/get', group.entityRef)
        })
        .then((entity: Entity) => {
          this.localState.entity = entity;
        })
        .catch(err => {
          this.localState.error = err;
        });
    },
    closeAdd() {
      this.localState.showAdd = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    _saveMembers(): Promise<GroupMember[]> {
      return this.$store.dispatch('groups/setMembers', this.localState.group)
        .then(members => {
          this.$store.commit('snackbar/showSuccess', 'Hooray, Success!');
          return members;
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    deleteUser(ug: GroupMember) {
      if (!this.localState.group) return;
      this.localState.group.users = 
        _filter(this.localState.group.users, l => l.user.username !== ug.user.username);
      this._saveMembers();
    },
    updateRole(upd: GroupMember) {
      if (!this.localState.group) return;
      this.localState.group.users = _concat(
        _filter(this.localState.group.users, l => l.user.username !== upd.user.username),
        upd
      );
      this._saveMembers();
    },
    addUser() {
      if (!this.localState.group) return;
      if (this.localState.editItem.user.username) {
        this.localState.group.users = 
          _concat(this.localState.group.users, this.localState.editItem);
      }
      this._saveMembers();
      this.closeAdd();
    }
  }
})
</script>