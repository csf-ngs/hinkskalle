<template>
  <div class="entities">
    <top-bar title="Entities"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator 
            id="entities"
            :items="entities"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading">
            <template v-slot:header>
              <v-toolbar flat>
                <v-text-field id="search" v-model="localState.search" prepend-icon="mdi-magnify" label="Search..." single-line hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-select class="mr-1"
                  v-model="localState.sortBy" 
                  label="Sort..."
                  hide-details 
                  :items="sortKeys"
                  item-text="desc"
                  item-value="key"
                  prepend-inner-icon="mdi-sort"></v-select>
                <v-btn-toggle dense active-class="green--text" borderless
                  v-model="localState.sortDesc" mandatory>
                  <v-btn :value="true"><v-icon>mdi-sort-descending</v-icon></v-btn>
                  <v-btn :value="false"><v-icon>mdi-sort-ascending</v-icon></v-btn>
                </v-btn-toggle>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn 
                      v-if="currentUser.isAdmin" 
                      id="create-entity" 
                      dense depressed
                      v-bind="attrs" v-on="on">Create Entity</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="name"
                              label="Name"
                              field="name"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="description"
                              label="Description"
                              field="description"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                        </v-row>
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              type="yesno"
                              label="Default Private"
                              field="defaultPrivate"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                        </v-row>
                        <v-row>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created"
                              :static-value="localState.editItem.createdAt | moment('YYYY-MM-DD HH:mm')"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created By"
                              :static-value="localState.editItem.createdBy"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="updatedAt"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn color="primary darken-1" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteEntityConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-spacer></v-spacer>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadEntities()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id" 
                  cols="12" md="6">
                  <v-card class="entity">
                    <router-link :to="{ name: 'EntityCollections', params: { entity: item.name } }" class="text-decoration-none">
                      <v-card-title class="headline">
                        <v-icon v-if="item.defaultPrivate">mdi-eye-off</v-icon>
                        {{item.name}}
                        ({{item.size}} {{item.size | pluralize('collection')}})
                      </v-card-title>
                    </router-link>
                    <v-divider></v-divider>
                    <v-list dense>
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description}}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.createdAt | moment('YYYY-MM-DD HH:mm')}} | {{item.createdBy}}
                          </v-list-item-title>
                          <v-list-item-subtitle>
                            Created
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <template v-if="item.canEdit(currentUser)">
                        <v-icon small class="mr-1" @click="editEntity(item)">mdi-pencil</v-icon>
                        <v-icon small @click="deleteEntity(item)">mdi-delete</v-icon>
                      </template>
                      <template v-else>
                        <v-icon small>mdi-cancel</v-icon>
                      </template>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </template>
          </v-data-iterator>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { Entity, User } from '../store/models';
import moment from 'moment';
import { clone as _clone } from 'lodash';

interface State {
  search: string;
  editItem: Entity;
  showEdit: boolean;
  showDelete: boolean;
  sortBy: string;
  sortDesc: boolean;
}

function defaultItem(): Entity {
  const item = new Entity();
  item.createdAt = new Date();
  return item;
}

export default Vue.extend({
  name: 'Entities',
  mounted() {
    this.loadEntities();
  },
  data: (): { localState: State; sortKeys: { key: string; desc: string }[] } => ({
    localState: {
      search: '',
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
      sortBy: 'name',
      sortDesc: false,
    },
    sortKeys: [
      { key: 'name', desc: 'Name' }, 
      { key :'createdAt', desc: "Create Date" }, 
      { key: 'updatedAt', desc: "Last Updated" },
      { key: 'size', desc: '# Collections' } 
    ]
  }),
  computed: {
    entities(): Entity[] {
      return this.$store.getters['entities/list'];
    },
    loading(): boolean {
      return this.$store.getters['entities/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Entity' : 'New Entity';
    },
    updatedAt(): string {
      return this.localState.editItem.updatedAt ?
        moment(this.localState.editItem.updatedAt).format('YYYY-MM-DD HH:mm') :
        '-';
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
  },
  watch: {
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        this.closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
      }
    },
  },
  methods: {
    loadEntities() {
      this.$store.dispatch('entities/list')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    editEntity(entity: Entity) {
      this.localState.editItem = _clone(entity);
      this.localState.showEdit = true;
    },
    deleteEntity(entity: Entity) {
      this.localState.editItem = _clone(entity);
      this.localState.showDelete = true;
    },
    deleteEntityConfirm() {
      this.$store.dispatch('entities/delete', this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', "It's gone!"))
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    save() {
      const action = this.localState.editItem.id ? 
        'entities/update' : 'entities/create';
      this.$store.dispatch(action, this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
  },
});
</script>