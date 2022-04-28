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
                @upted="localState.group=$event"></hsk-text-input>
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
                @upted="localState.group=$event"></hsk-text-input>
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
            >
            <template v-slot:item.user.username="{ item }">
              {{item.user.username}}
            </template>
            <template v-slot:item.user.lastname="{ item }">
              {{item.user.firstname}} {{item.user.lastname}}
            </template>
            <template v-slot:item.role="{ item }">
              {{item.role}}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon small @click="editMember(item)">mdi-pencil</v-icon>
              <v-icon small @click="deleteMember(item)">mdi-delete</v-icon>
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
import { Entity, Group, User } from '../store/models';

interface State {
  group: Group | null;
  entity: Entity | null;
  error: string | null;
}

export default Vue.extend({
  name: 'GroupDetails',
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
    }
  }),
  watch: {
    $route() {
      this.loadGroup();
    }
  },
  computed: {
    loading(): boolean {
      return this.$store.getters['container/status']==='loading';
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return this.localState.group !== null && this.localState.group.canEdit(this.currentUser)
    },
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
    }
  }
})
</script>